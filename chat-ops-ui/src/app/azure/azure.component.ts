import { Component } from '@angular/core';
import { VMComponent } from "./../vm/vm.component";
import { AzureService } from "./azure.service";


@Component({
  selector: 'app-azure',
  templateUrl: './../vm/vm.component.html',
  styleUrls: ['./../vm/vm.component.css']
})
export class AzureComponent extends VMComponent {
  service = AzureService;
  constructor(vmService: AzureService) {
    super();
    this.vmService = vmService;
  }
}