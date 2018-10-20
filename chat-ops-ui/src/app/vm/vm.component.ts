import { Component, OnInit } from '@angular/core';
import { VMService } from "./vm.service";
import { VM } from "./vm";


@Component({
  selector: 'app-aws',
  templateUrl: './../vm/vm.component.html',
  styleUrls: ['./../vm/vm.component.css']
})
export abstract class VMComponent implements OnInit {

  vmService !: VMService;
  errorMessage: string;
  vms: VM[];

  constructor() {
    this.vms = [];
  }

  getVMs(): void {
    this.vmService
        .getVMs()
        .toPromise()
        .then(
            vms => {
                this.vms = vms;
            }
        );
  }

  deleteVM(vm: VM): void {
    this.vmService
        .deleteVM(vm)
        .toPromise();
  }

  refreshVMs(period: number): void {
    this.vmService
        .refreshVMs(period)
        .subscribe(
          vms => {
            this.vms = vms;
          },
          error => this.errorMessage = <any>error
        );
  }

  ngOnInit() {
    this.getVMs();
    this.refreshVMs(5000);
  }
}
