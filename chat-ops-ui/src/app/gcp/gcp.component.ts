import { Component } from '@angular/core';
import { VMComponent } from "./../vm/vm.component";
import { GCPService } from "./gcp.service";


@Component({
  selector: 'app-gcp',
  templateUrl: './../vm/vm.component.html',
  styleUrls: ['./../vm/vm.component.css']
})
export class GCPComponent extends VMComponent {
  service = GCPService;
  constructor(vmService: GCPService) {
    super();
    this.vmService = vmService;
  }
}