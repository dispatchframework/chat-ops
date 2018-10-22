import { ModuleWithProviders } from '@angular/core/src/metadata/ng_module';
import { Routes, RouterModule } from '@angular/router';

import { AWSComponent } from './aws/aws.component';
import { GCPComponent } from './gcp/gcp.component';
import { AzureComponent } from './azure/azure.component';
import { VMwareComponent } from './vmware/vmware.component';


export const ROUTES: Routes = [
    {path: '', redirectTo: 'aws', pathMatch: 'full'},
    {path: 'aws', component: AWSComponent},
    {path: 'gcp', component: GCPComponent},
    {path: 'azure', component: AzureComponent},
    {path: 'vmware', component: VMwareComponent}
];

export const ROUTING: ModuleWithProviders = RouterModule.forRoot(ROUTES);